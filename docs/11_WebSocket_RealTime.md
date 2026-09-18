# Scan2Pay — WebSocket Real-Time Payment Updates

> Replaces the 1.5s polling on `/charge` and `/pay/[reference]` with
> on-demand WebSocket connections that live only for the duration of an
> active payment window (max 6 minutes).

---

## Why WebSockets

### The polling problem

Before this change, two pages polled the API every 1.5 seconds:

| Page | Endpoint polled | Who polls | Purpose |
|---|---|---|---|
| `/charge` | `GET /payments/:txn_id` | Merchant (JWT) | Detect payment success after charge created |
| `/pay/[reference]` | `GET /pay/:reference` | Customer (public) | Detect payment completion on customer device |

For a 5-minute charge window that is ~200 Lambda invocations per charge session,
each hitting Supabase. As merchant volume grows this compounds — 50 active
charge sessions simultaneously = 10,000 invocations in 5 minutes just for polling.

### What WebSockets give us

- Webhook fires → backend pushes `PAYMENT_SUCCESS` to the exact connection
  waiting for that transaction → frontend reacts instantly
- Zero polling invocations
- Connection lives for at most 6 minutes per payment window, then closes
- No always-on connections — nothing is open outside an active payment

---

## Architecture Overview

```
Merchant creates charge (POST /charges)
    ↓
Frontend opens WebSocket connection
wss://WS_API/Prod?txn_id=txn_000063&token=<jwt>
    ↓
$connect Lambda → stores { connectionId, txn_id, merchant_id, ttl } in DynamoDB
    ↓
Customer scans QR → pays via Paystack popup
    ↓
Paystack fires webhook → POST /webhooks/paystack (existing Scan2PayApiFunction)
    ↓
_handle_charge_success() → reads connectionId from DynamoDB by txn_id
    ↓
PostToConnection({ type: "PAYMENT_SUCCESS", txn_id, amount_cents })
    ↓
Frontend receives message → shows "Paid ✓" → closes WebSocket
    ↓
$disconnect Lambda → deletes connectionId from DynamoDB
```

---

## Infrastructure Added

### New AWS resources (template.yaml)

| Resource | Type | Purpose |
|---|---|---|
| `Scan2PayWebSocketApi` | `AWS::ApiGatewayV2::Api` | WebSocket API Gateway (separate from HTTP API) |
| `WebSocketConnectionsTable` | `AWS::DynamoDB::Table` | Stores active connections (connectionId PK, ttl, GSIs) |
| `WebSocketConnectFunction` | `AWS::Serverless::Function` | Handles `$connect` — validates token, writes to DynamoDB |
| `WebSocketDisconnectFunction` | `AWS::Serverless::Function` | Handles `$disconnect` — deletes from DynamoDB |

### DynamoDB table: `websocket_connections`

```
connectionId  (PK, text)   — assigned by API Gateway on connect
merchant_id   (text)       — set for charge page connections (JWT auth)
txn_id        (text)       — set for both charge page and pay page connections
connected_at  (text)       — ISO timestamp
ttl           (number)     — Unix epoch + 6 minutes — auto-deleted by DynamoDB TTL
```

**GSIs:**
- `txn_id-index` — used by webhook broadcast to find connectionId by txn_id
- `merchant_id-index` — reserved for future use (e.g. push other merchant events)

**Why DynamoDB and not Supabase:**
Connection rows are ephemeral infrastructure state, not business data. They live
for seconds to minutes. DynamoDB TTL auto-cleans them with no cron needed.
This table is fully decoupled from the business database — if Supabase is replaced
with RDS or Aurora tomorrow, the WebSocket layer is unchanged. PAY_PER_REQUEST
billing means cost is effectively zero at current scale.

### New Python files

```
app/
├── api/
│   └── routes/
│       └── websocket.py          # $connect and $disconnect handlers
└── services/
    └── websocket_broadcast.py    # broadcast utility used by webhooks.py
```

### Modified files

```
app/api/routes/webhooks.py        # 4 lines added to _handle_charge_success()
template.yaml                     # WebSocket API GW + DynamoDB + 2 new Lambdas
```

---

## Connection Lifecycle

### Charge page (`/charge`) — merchant authenticated

```
1. Merchant types amount → taps "Create charge"
2. POST /charges → { txn_id, qr_reference, expires_at, ... }
3. Frontend opens: wss://WS_URL/Prod?txn_id=txn_000063&token=<jwt>
4. $connect Lambda:
   - verifies JWT → extracts merchant_id
   - writes { connectionId, txn_id, merchant_id, ttl: now+6min } to DynamoDB
   - returns 200
5. Frontend waits (no polling)
6. Customer pays → webhook fires → PAYMENT_SUCCESS pushed
7. Frontend shows "Paid ✓" → closes WebSocket
8. $disconnect Lambda deletes connectionId from DynamoDB

OR: 6 minutes pass with no payment
7. Frontend closes WebSocket (setTimeout 6 min)
8. $disconnect Lambda deletes connectionId
9. ExpireChargesFunction cron marks transaction failed (unchanged)
```

### Pay page (`/pay/[reference]`) — public, no auth

```
1. Customer lands on /pay/QR-890E282B
2. GET /pay/:reference → resolves code, gets charge_session.txn_id if active
3. Customer enters amount (or sees fixed amount) → taps Pay
4. POST /pay/:reference/initialise → { txn_id, access_code, amount_cents }
5. Frontend opens: wss://WS_URL/Prod?txn_id=txn_000063
   (no token — pay page is public)
6. $connect Lambda:
   - no JWT verification (txn_id only connection)
   - writes { connectionId, txn_id, ttl: now+6min } to DynamoDB
   - returns 200
7. Paystack popup opens → customer pays
8. Webhook fires → PAYMENT_SUCCESS pushed
9. Frontend shows success screen → closes WebSocket
```

---

## WebSocket Endpoints

### WebSocket URL

```
wss://{WS_API_ID}.execute-api.af-south-1.amazonaws.com/Prod
```

Exposed as `NEXT_PUBLIC_WS_URL` in the frontend `.env`.

### Connection query parameters

| Parameter | Required | Who sends it | Purpose |
|---|---|---|---|
| `txn_id` | Always | Both pages | Scopes the connection to a specific transaction |
| `token` | Charge page only | Merchant | JWT access token for auth |

### Message types (server → client)

**`PAYMENT_SUCCESS`**
```json
{
  "type": "PAYMENT_SUCCESS",
  "txn_id": "txn_000063367CFA",
  "amount_cents": 8500,
  "paid_at": "2026-09-20T14:32:11Z"
}
```

Sent when `_handle_charge_success()` in `webhooks.py` processes a
`charge.success` event from Paystack and finds an active WebSocket connection
for that transaction.

---

## Backend Implementation

### `app/services/websocket_broadcast.py`

```python
import json
import logging
import boto3
from botocore.exceptions import ClientError
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_dynamodb = None
_apigw = None


def _get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb", region_name="af-south-1")
    return _dynamodb


def _get_apigw():
    global _apigw
    if _apigw is None:
        settings = get_settings()
        _apigw = boto3.client(
            "apigatewaymanagementapi",
            endpoint_url=settings.websocket_endpoint,
            region_name="af-south-1",
        )
    return _apigw


def broadcast_to_txn(txn_id: str, message: dict) -> None:
    """Push a message to all WebSocket connections waiting on txn_id."""
    settings = get_settings()
    if not settings.websocket_endpoint or not settings.ws_connections_table:
        return  # WebSocket not configured — silently skip (dev without WS)

    try:
        table = _get_dynamodb().Table(settings.ws_connections_table)
        result = table.query(
            IndexName="txn_id-index",
            KeyConditionExpression="txn_id = :tid",
            ExpressionAttributeValues={":tid": txn_id},
        )
        connections = result.get("Items", [])
        if not connections:
            return

        payload = json.dumps(message).encode()
        apigw = _get_apigw()

        for conn in connections:
            connection_id = conn["connectionId"]
            try:
                apigw.post_to_connection(ConnectionId=connection_id, Data=payload)
                logger.info("ws: pushed %s to %s", message.get("type"), connection_id)
            except ClientError as e:
                if e.response["Error"]["Code"] == "GoneException":
                    # stale connection — delete it
                    table.delete_item(Key={"connectionId": connection_id})
                    logger.info("ws: removed stale connection %s", connection_id)
                else:
                    logger.warning("ws: post_to_connection error: %s", e)
    except Exception as e:
        logger.error("ws: broadcast_to_txn failed: %s", e)
        # never raise — a failed push must not break the webhook response
```

### `app/api/routes/websocket.py`

```python
import time
from fastapi import APIRouter
from mangum import Mangum
from app.core.security import decode_token
from app.core.config import get_settings
import boto3

router = APIRouter()
TTL_SECONDS = 6 * 60  # 6 minutes


def _table():
    settings = get_settings()
    return boto3.resource("dynamodb", region_name="af-south-1").Table(
        settings.ws_connections_table
    )


def handle_connect(event: dict) -> dict:
    """
    Called by the WebSocket $connect Lambda (not via FastAPI router).
    Validates token if present, stores connection in DynamoDB.
    """
    connection_id = event["requestContext"]["connectionId"]
    params = event.get("queryStringParameters") or {}
    txn_id = params.get("txn_id")
    token = params.get("token")

    if not txn_id:
        return {"statusCode": 400}

    merchant_id = None
    if token:
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return {"statusCode": 401}
        # merchant_id resolved later from user_id if needed
        # for now store user_id as merchant_id placeholder
        merchant_id = payload.get("sub")

    _table().put_item(Item={
        "connectionId": connection_id,
        "txn_id": txn_id,
        "merchant_id": merchant_id,
        "connected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ttl": int(time.time()) + TTL_SECONDS,
    })
    return {"statusCode": 200}


def handle_disconnect(event: dict) -> dict:
    """Called by the WebSocket $disconnect Lambda."""
    connection_id = event["requestContext"]["connectionId"]
    _table().delete_item(Key={"connectionId": connection_id})
    return {"statusCode": 200}
```

### Changes to `webhooks.py` — `_handle_charge_success()`

Add 4 lines after the transaction is marked success:

```python
# existing line:
db.table("transactions").update(updates).eq("id", txn["id"]).execute()

# NEW — push to WebSocket if a connection is waiting
from app.services.websocket_broadcast import broadcast_to_txn
broadcast_to_txn(txn["id"], {
    "type": "PAYMENT_SUCCESS",
    "txn_id": txn["id"],
    "amount_cents": data.get("amount"),
    "paid_at": updates.get("paid_at"),
})
```

### `template.yaml` additions

```yaml
# ── WebSocket API Gateway ────────────────────────────────────────────────────
Scan2PayWebSocketApi:
  Type: AWS::ApiGatewayV2::Api
  Properties:
    Name: Scan2PayWebSocketAPI
    ProtocolType: WEBSOCKET
    RouteSelectionExpression: "$request.body.action"

# ── WebSocket Connections Table (DynamoDB) ───────────────────────────────────
WebSocketConnectionsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub 'scan2pay-ws-connections-${Environment}'
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: connectionId
        AttributeType: S
      - AttributeName: txn_id
        AttributeType: S
      - AttributeName: merchant_id
        AttributeType: S
    KeySchema:
      - AttributeName: connectionId
        KeyType: HASH
    GlobalSecondaryIndexes:
      - IndexName: txn_id-index
        KeySchema:
          - AttributeName: txn_id
            KeyType: HASH
        Projection:
          ProjectionType: ALL
      - IndexName: merchant_id-index
        KeySchema:
          - AttributeName: merchant_id
            KeyType: HASH
        Projection:
          ProjectionType: ALL
    TimeToLiveSpecification:
      AttributeName: ttl
      Enabled: true

# ── $connect Lambda ──────────────────────────────────────────────────────────
WebSocketConnectFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: app.ws.connect.handler
    CodeUri: .
    Description: WebSocket $connect — validate token, store connection
    MemorySize: 128
    Timeout: 10
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref WebSocketConnectionsTable
    Environment:
      Variables:
        WS_CONNECTIONS_TABLE: !Ref WebSocketConnectionsTable

# ── $disconnect Lambda ───────────────────────────────────────────────────────
WebSocketDisconnectFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: app.ws.disconnect.handler
    CodeUri: .
    Description: WebSocket $disconnect — remove connection from DynamoDB
    MemorySize: 128
    Timeout: 10
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref WebSocketConnectionsTable
    Environment:
      Variables:
        WS_CONNECTIONS_TABLE: !Ref WebSocketConnectionsTable

# ── Scan2PayApiFunction gets WS broadcast permissions ────────────────────────
# Add to existing Scan2PayApiFunction policies:
#   - DynamoDBReadPolicy: TableName: !Ref WebSocketConnectionsTable
#   - Statement: execute-api:ManageConnections on WebSocket API ARN
# Add to existing Scan2PayApiFunction environment:
#   WS_CONNECTIONS_TABLE: !Ref WebSocketConnectionsTable
#   WEBSOCKET_ENDPOINT: !Sub "https://${Scan2PayWebSocketApi}.execute-api.${AWS::Region}.amazonaws.com/Prod"
```

---

## Frontend Implementation

### Environment variable

```env
NEXT_PUBLIC_WS_URL=wss://{WS_API_ID}.execute-api.af-south-1.amazonaws.com/Prod
```

### `useChargeWebSocket` hook

```typescript
// hooks/useChargeWebSocket.ts
import { useEffect, useRef } from "react"

const WS_URL = process.env.NEXT_PUBLIC_WS_URL!
const TIMEOUT_MS = 6 * 60 * 1000  // 6 minutes

export function useChargeWebSocket(
  txnId: string | null,
  onPaymentSuccess: (data: { amount_cents: number; paid_at: string }) => void
) {
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!txnId) return  // no connection until charge exists

    const token = localStorage.getItem("accessToken")
    const ws = new WebSocket(`${WS_URL}?txn_id=${txnId}&token=${token}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.type === "PAYMENT_SUCCESS") {
        onPaymentSuccess({ amount_cents: msg.amount_cents, paid_at: msg.paid_at })
        ws.close()
      }
    }

    ws.onerror = () => ws.close()

    // close after 6 minutes regardless
    const expiry = setTimeout(() => ws.close(), TIMEOUT_MS)

    return () => {
      clearTimeout(expiry)
      ws.close()
    }
  }, [txnId])  // re-runs only when a new charge is created
}
```

### `usePayWebSocket` hook

```typescript
// hooks/usePayWebSocket.ts
import { useEffect } from "react"

const WS_URL = process.env.NEXT_PUBLIC_WS_URL!
const TIMEOUT_MS = 6 * 60 * 1000

export function usePayWebSocket(
  txnId: string | null,
  onPaymentSuccess: (data: { amount_cents: number; paid_at: string }) => void
) {
  useEffect(() => {
    if (!txnId) return  // no connection until initialise succeeds

    // no token — pay page is public
    const ws = new WebSocket(`${WS_URL}?txn_id=${txnId}`)

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.type === "PAYMENT_SUCCESS") {
        onPaymentSuccess({ amount_cents: msg.amount_cents, paid_at: msg.paid_at })
        ws.close()
      }
    }

    ws.onerror = () => ws.close()

    const expiry = setTimeout(() => ws.close(), TIMEOUT_MS)

    return () => {
      clearTimeout(expiry)
      ws.close()
    }
  }, [txnId])
}
```

### Usage on `/charge` page

```typescript
// Replace the existing useEffect polling block with:
const [txnId, setTxnId] = useState<string | null>(null)

useChargeWebSocket(txnId, ({ amount_cents, paid_at }) => {
  setChargeStatus("paid")
  // existing paid UI logic
})

// when charge is created:
const result = await createCharge({ amount_cents, label })
setTxnId(result.txn_id)  // this triggers the WebSocket connection
```

### Usage on `/pay/[reference]` page

```typescript
// Replace the existing polling block with:
const [txnId, setTxnId] = useState<string | null>(null)

usePayWebSocket(txnId, ({ amount_cents, paid_at }) => {
  setPaymentStatus("success")
  // existing success UI logic
})

// when initialise succeeds:
const result = await initialisePayment({ reference, amount_cents, customer_email })
setTxnId(result.txn_id)  // this triggers the WebSocket connection
```

---

## What Is NOT Changed

- `GET /payments/:txn_id` endpoint stays — used by admin and transaction detail views
- `GET /pay/:reference` endpoint stays — used for initial QR resolution
- `ExpireChargesFunction` cron stays — still marks expired charge sessions as failed
- `ReconcilePaystackFunction` cron stays — still catches missed webhooks
- All existing polling code can be removed from the two frontend pages once
  WebSocket hooks are confirmed working in staging

---

## Rollout Plan

1. Backend: add DynamoDB table + 2 Lambda handlers + broadcast service + webhook wire-up → deploy
2. Frontend: add `useChargeWebSocket` and `usePayWebSocket` hooks
3. Test in staging: create charge → pay → confirm PAYMENT_SUCCESS received
4. Keep polling as fallback for 1 sprint (run both in parallel, polling as safety net)
5. Remove polling once WebSocket confirmed stable in prod

---

## Cost Impact

| | Polling (before) | WebSocket (after) |
|---|---|---|
| Invocations per charge session | ~240 (1.5s × 6min) | 2 ($connect + $disconnect) |
| Compute per charge session | ~48s (240 × 200ms) | ~0.1s |
| API Gateway cost | HTTP request per poll | $0.000003/connection-min + $0.000001/message |
| DynamoDB | None | PAY_PER_REQUEST, ~$0.00 at current scale |

At 1,000 charge sessions/month the saving is small in absolute dollars.
At 10,000+ sessions/month the Lambda compute saving becomes meaningful.

---

## New SSM Parameters Required

```
/scan2pay/{env}/WEBSOCKET_ENDPOINT   → https://{WS_API_ID}.execute-api.af-south-1.amazonaws.com/Prod
/scan2pay/{env}/WS_CONNECTIONS_TABLE → scan2pay-ws-connections-{env}
```

Both added to `deploy.sh` `ssm_put` calls.
