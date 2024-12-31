<?php
function getCanonicalModelName($modelName, $jsonFile = 'Models.json')
{
  // Read and decode the JSON file
  if (!file_exists($jsonFile)) {
    fwrite(STDERR, "Error: The file '$jsonFile' was not found.\n");
    exit(1);
  }

  $jsonContent = file_get_contents($jsonFile);
  $models = json_decode($jsonContent, true);

  if ($models === null && json_last_error() !== JSON_ERROR_NONE) {
    fwrite(STDERR, "Error: The file '$jsonFile' contains invalid JSON.\n");
    exit(1);
  }

  // Check if the model name is a canonical name
  if (array_key_exists($modelName, $models)) {
    return $modelName;
  }

  // Search through aliases
  foreach ($models as $canonicalName => $details) {
    if (isset($details['alias']) && $details['alias'] === $modelName) {
      return $canonicalName;
    }
  }

  // Model name not found
  return null;
}

if (php_sapi_name() === 'cli') {
  if ($argc !== 2) {
    fwrite(STDERR, "Usage: php get_canonical_model.php <model_name>\n");
    exit(1);
  }

  $modelNameInput = trim($argv[1]);
  $canonicalName = getCanonicalModelName($modelNameInput);

  if ($canonicalName) {
    echo "$canonicalName\n";
  } else {
    fwrite(STDERR, "Canonical Model for '$modelNameInput' not found\n");
    exit(1);
  }
}
