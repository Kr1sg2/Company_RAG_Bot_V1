# PowerShell script to rename files using underscores instead of hyphens

# Navigate to the specified directory
Set-Location -Path "C:\CB_FS01"

# Get all files in the current directory
Get-ChildItem -File | ForEach-Object {
    $originalName = $_.Name

    # Convert to lowercase
    $newName = $originalName.ToLower()

    # Replace spaces with underscores
    $newName = $newName -replace ' ', '_'

    # Remove special characters except letters, numbers, underscores, and periods
    $newName = $newName -replace '[^a-z0-9_\.]', ''

    # Check if the new name is different from the original
    if ($newName -ne $originalName) {
        # Rename the file
        Rename-Item -Path $_.FullName -NewName $newName
        Write-Output "Renamed: '$originalName' to '$newName'"
    }
}
