<?php
$target = __DIR__ . '/cache_site';

function deleteFolder($folder) {
    if (!is_dir($folder)) return false;
    $items = scandir($folder);
    foreach ($items as $item) {
        if ($item === '.' || $item === '..') continue;
        $path = "$folder/$item";
        if (is_dir($path)) {
            deleteFolder($path);
        } else {
            unlink($path);
        }
    }
    return rmdir($folder);
}

if (deleteFolder($target)) {
    echo "✅ cache_site deleted successfully.";
} else {
    echo "❌ Failed to delete cache_site.";
}
?>
