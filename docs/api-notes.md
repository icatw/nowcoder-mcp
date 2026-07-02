# Nowcoder API Notes

The MVP uses public web endpoints observed from Nowcoder pages.

## Search

```text
POST https://gw-c.nowcoder.com/api/sparta/pc/search
```

Payload fields used:

- `type`: `all`
- `query`: search keyword
- `page`: page number
- `tag`: optional tag list
- `order`: empty string for relevance/default, `create` for latest

Known tag IDs:

- `818`: 面经
- `861`: 求职进度
- `823`: 内推
- `856`: 公司评价

## Discuss detail

```text
GET https://gw-c.nowcoder.com/api/sparta/detail/content-data/detail/{content_id}
```

## Feed detail

```text
GET https://www.nowcoder.com/feed/main/detail/{uuid}
```

Feed detail may require HTML parsing or embedded JSON extraction. Some public feed pages can return an accessible page with empty extracted title/content, so phase-2 analysis workflows should prefer discuss `content_id` sources when available and treat empty feed extraction as a low-confidence/no-content source rather than inventing signals.

## Risk

These are public web endpoints, not a documented stable API. Keep parsing isolated in `client.py` and cover expected shapes with fixtures.
