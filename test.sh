if gh release view "$VERSION" > /dev/null 2>&1; then
    echo "skip_publish=true"
else
    echo "skip_publish=false"
fi

