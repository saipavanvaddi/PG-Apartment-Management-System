-- Enable RLS
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Allow public uploads to newvisitorbucket"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'newvisitorbucket'
  AND auth.role() = 'anon'
);

CREATE POLICY "Allow public read of newvisitorbucket"
ON storage.objects FOR SELECT
USING (
  bucket_id = 'newvisitorbucket'
);

-- Grant usage on storage schema
GRANT USAGE ON SCHEMA storage TO anon;

-- Grant select on objects to anon
GRANT SELECT ON storage.objects TO anon;

-- Grant insert on objects to anon
GRANT INSERT ON storage.objects TO anon; 