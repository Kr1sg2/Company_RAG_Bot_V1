# PowerShell script to rename files using hyphens instead of other punctuation, spaces, and periods

# Navigate to the specified directory
Set-Location -Path "C:\CB_FS01"

# Get all files in the current directory
Get-ChildItem -File | ForEach-Object {
    $originalName = $_.Name

    # Split the file name and extension
    $name, $extension = [System.IO.Path]::GetFileNameWithoutExtension($originalName), [System.IO.Path]::GetExtension($originalName)

    # Convert to lowercase
    $newName = $name.ToLower()

    # Replace spaces with hyphens
    $newName = $newName -replace ' ', '-'

    # Replace underscores with hyphens
    $newName = $newName -replace '_', '-'

    # Replace other punctuation with hyphens
    $newName = $newName -replace '[^\w\s-]', '-'

    # Combine the new name with the original extension
    $newName = "$newName$extension"

    # Check if the new name is different from the original
    if ($newName -ne $originalName) {
        # Rename the file
        Rename-Item -Path $_.FullName -NewName $newName
        Write-Output "Renamed: '$originalName' to '$newName'"
    }
}