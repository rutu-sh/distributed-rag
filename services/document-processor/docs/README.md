# Document Processor

## POST
- URL - `/process/uuid_test2 `
- add PDF file to body, `Content-Type: application/pdf`
- response - 
    ```json
    {
    "chunk count": 28,
    "filename": "test.pdf",
    "content_type": "application/pdf",
    "size_kb": 64.66
    }
    ```