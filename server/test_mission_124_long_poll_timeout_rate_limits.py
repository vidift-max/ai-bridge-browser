"""Mission 124: Long Poll timeout, cursor, batch, and rate-limit behavior."""
import json, os, tempfile, threading, time, unittest
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.rate_limit import SlidingWindowRateLimiter
from server.sqlite_store import SQLiteMessengerStore

class Mission124LongPollTimeoutAndRateLimitTest(unittest.TestCase):
    def setUp(self):
        self.db = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False); self.db.close()
        self.tokens = {"synthetic-token-ai01":"AI-01","synthetic-token-ai02":"AI-02","synthetic-token-ai03":"AI-03"}
        self._start_runtime(60)
    def _start_runtime(self, max_events):
        self.auth=Authenticator(self.tokens); self.store=SQLiteMessengerStore(self.db.name)
        self.backend=MessengerBackend(self.tokens,{"default":{"AI-01","AI-02"}},self.store,authenticator=self.auth)
        MessengerHandler.backend=self.backend; MessengerHandler.authenticator=self.auth
        MessengerHandler.rate_limiter=SlidingWindowRateLimiter(max_events=max_events,window_seconds=60)
        MessengerHandler.operational=None; MessengerHandler.audio_store=None; MessengerHandler.voice_control=None
        self.server=ThreadingHTTPServer(("127.0.0.1",0),MessengerHandler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
    def _stop_runtime(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2); self.backend.close()
    def tearDown(self):
        self._stop_runtime()
        MessengerHandler.backend=None; MessengerHandler.authenticator=None
        MessengerHandler.operational=None; MessengerHandler.audio_store=None; MessengerHandler.voice_control=None
        os.unlink(self.db.name)
    def request(self,method,path,token="synthetic-token-ai02",payload=None,timeout=5):
        c=HTTPConnection("127.0.0.1",self.server.server_port,timeout=timeout); h={}
        if token is not None: h["Authorization"]="Bearer "+token
        body=None
        if payload is not None: body=json.dumps(payload); h["Content-Type"]="application/json"
        c.request(method,path,body=body,headers=h); r=c.getresponse()
        data=json.loads(r.read().decode("utf-8")); c.close(); return r.status,data
    def send(self,message_id,request_id):
        return self.request("POST","/v1/messages","synthetic-token-ai01",{
            "messageId":message_id,"conversationId":"default","recipientAiIds":["AI-02"],
            "body":message_id,"clientRequestId":request_id})
    def poll(self,after=0,limit=10,timeout=0,token="synthetic-token-ai02"):
        return self.request("GET",f"/v1/conversations/default/messages/wait?after={after}&limit={limit}&timeout={timeout}",
                            token,timeout=max(5,timeout+2))
    def test_nonempty_wait_returns_after_configured_timeout(self):
        start=time.monotonic(); status,result=self.poll(timeout=1); elapsed=time.monotonic()-start
        self.assertEqual((status,result["messages"]),(200,[])); self.assertGreaterEqual(elapsed,.85); self.assertLess(elapsed,2.5)
    def test_message_arriving_during_wait_wakes_poll_early(self):
        with ThreadPoolExecutor(max_workers=1) as pool:
            start=time.monotonic(); waiting=pool.submit(self.poll,0,10,4); time.sleep(.2)
            send_status,sent=self.send("m124-wakeup","m124-wakeup-request"); poll_status,received=waiting.result(timeout=5)
        self.assertEqual((send_status,poll_status),(200,200)); self.assertEqual(received["messages"][0]["messageId"],sent["messageId"])
        self.assertLess(time.monotonic()-start,2.0)
    def test_future_cursor_does_not_replay_older_messages(self):
        self.send("m124-future-cursor","m124-future-cursor-request")
        status,result=self.poll(after=999); self.assertEqual((status,result["messages"]),(200,[]))
    def test_maximum_batch_limit_is_accepted(self):
        status,result=self.poll(limit=100); self.assertEqual((status,result["messages"]),(200,[]))
    def test_single_item_batches_page_without_overlap(self):
        self.send("m124-page-1","m124-page-request-1"); self.send("m124-page-2","m124-page-request-2")
        s1,a=self.poll(limit=1); s2,b=self.poll(after=a["messages"][0]["sequence"],limit=1)
        self.assertEqual((s1,s2),(200,200)); self.assertEqual(a["messages"][0]["messageId"],"m124-page-1")
        self.assertEqual(b["messages"][0]["messageId"],"m124-page-2")
        self.assertGreater(b["messages"][0]["sequence"],a["messages"][0]["sequence"])
    def test_unacknowledged_redelivery_is_stable_across_polls(self):
        self.send("m124-redelivery","m124-redelivery-request"); s1,a=self.poll(); s2,b=self.poll()
        self.assertEqual((s1,s2),(200,200)); self.assertEqual(a["messages"][0]["messageId"],b["messages"][0]["messageId"])
        self.assertEqual(a["messages"][0]["sequence"],b["messages"][0]["sequence"])
    def test_acknowledged_item_does_not_reappear(self):
        self.send("m124-no-reappear","m124-no-reappear-request")
        sa,ack=self.request("POST","/v1/messages/m124-no-reappear/ack","synthetic-token-ai02",{})
        sp,result=self.poll(); self.assertEqual((sa,ack["state"]),(200,"ACKNOWLEDGED"))
        self.assertEqual((sp,result["messages"]),(200,[]))
    def test_rate_limit_returns_429_after_principal_budget(self):
        self._stop_runtime(); self._start_runtime(2)
        self.assertEqual(self.poll()[0],200); self.assertEqual(self.poll()[0],200)
        status,result=self.poll(); self.assertEqual((status,result["error"]),(429,"rate_limit_exceeded"))
    def test_rate_limit_budget_is_isolated_between_ai_principals(self):
        self._stop_runtime(); self._start_runtime(2)
        self.assertEqual(self.poll()[0],200); self.assertEqual(self.poll()[0],200); self.assertEqual(self.poll()[0],429)
        a=self.send("m124-ai01-budget-1","m124-ai01-budget-request-1")
        b=self.send("m124-ai01-budget-2","m124-ai01-budget-request-2")
        self.assertEqual((a[0],b[0]),(200,200))
    def test_concurrent_requests_cannot_exceed_one_event_budget(self):
        self._stop_runtime(); self._start_runtime(1); barrier=threading.Barrier(3)
        def call():
            barrier.wait(timeout=3); return self.poll(timeout=0)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(call); b=pool.submit(call); barrier.wait(timeout=3)
            results=[a.result(timeout=5),b.result(timeout=5)]
        self.assertEqual(sorted(status for status,_ in results),[200,429])
        rejected=next(result for status,result in results if status==429)
        self.assertEqual(rejected["error"],"rate_limit_exceeded")

if __name__=="__main__": unittest.main()
