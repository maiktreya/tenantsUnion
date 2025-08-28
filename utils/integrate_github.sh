#!/bin/bash
curl --request GET \
--url "https://api.github.com/octocat" \
--header "Authorization: Bearer YOUR-TOKEN" \ # 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
--header "X-GitHub-Api-Version: 2022-11-28"