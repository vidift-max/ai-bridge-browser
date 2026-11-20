# WebView Boundary

WebView instances remain UI/runtime objects. Durable identity belongs to the browser state model; WebView instances are recreated from that state.

No WebView object is persisted. No page credential or page content is persisted by this model.