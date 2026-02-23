param(
    [Parameter(Mandatory=$true)]
    [string]$file,

    [Parameter(Mandatory=$true)]
    [string]$msg
)

git add $file
git commit -m $msg
git push
