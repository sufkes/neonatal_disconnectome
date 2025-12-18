#!/bin/bash
echo "Generating checksums..."
for file in *.tar.gz; do
    if [ -f "$file" ]; then
        checksum=$(md5 -q "$file" 2>/dev/null || md5sum "$file" | cut -d' ' -f1)
        size=$(du -m "$file" | cut -f1)
        echo "$file:"
        echo "  MD5: $checksum"
        echo "  Size: ${size}MB"
        echo ""
    fi
done
