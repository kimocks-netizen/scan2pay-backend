-- Drop the old slot check constraint that only allowed 4 values
ALTER TABLE cms_assets DROP CONSTRAINT IF EXISTS cms_assets_slot_check;

-- Add new columns if not already present
ALTER TABLE cms_assets ADD COLUMN IF NOT EXISTS visible boolean DEFAULT true;
ALTER TABLE cms_assets ADD COLUMN IF NOT EXISTS focal_x float8 DEFAULT 50;
ALTER TABLE cms_assets ADD COLUMN IF NOT EXISTS focal_y float8 DEFAULT 50;

-- Backfill existing rows
UPDATE cms_assets SET visible = true WHERE visible IS NULL;
UPDATE cms_assets SET focal_x = 50 WHERE focal_x IS NULL;
UPDATE cms_assets SET focal_y = 50 WHERE focal_y IS NULL;
