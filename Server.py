
class TThreadPoolServer2(TServer):
    """Server with a fixed size pool of threads which service requests."""

    def __init__(self, *args, **kwargs):
        TServer.__init__(self, *args)
        self.clients = queue.Queue()
        self.threads = 10
        self.daemon = kwargs.get("daemon", False)
        self.exit_ent=multiprocessing.Event()
        self.worker=[]

    def setNumThreads(self, num):
        """Set the number of worker threads that should be created"""
        self.threads = num

    def serveThread(self):
        """Loop around getting clients from the shared queue and process them."""
        while self.exit_ent.is_set() is False:
            try:
                client = self.clients.get(block=True,timeout=1)
                if client:
                    self.serveClient(client)
            except Exception as x:
                pass

    def serveClient(self, client):
        """Process input/output from a client for as long as possible"""
        itrans = self.inputTransportFactory.getTransport(client)
        otrans = self.outputTransportFactory.getTransport(client)
        iprot = self.inputProtocolFactory.getProtocol(itrans)
        oprot = self.outputProtocolFactory.getProtocol(otrans)
        try:
            while self.exit_ent.is_set() is False:
                self.processor.process(iprot, oprot)
        except :
            pass


        itrans.close()
        otrans.close()

    def stop(self):
        self.exit_ent.set()
        self.serverTransport.close()
        for t in self.worker:
            t.join()
        self.worker.clear()
        self.exit_ent.clear()

    def serve(self):
        """Start a fixed number of worker threads and put client into a queue"""
        for i in range(self.threads):
            try:
                t = threading.Thread(target=self.serveThread)
                t.setDaemon(self.daemon)
                t.start()
                self.worker.append(t)
            except :
                pass

        # Pump the socket for clients
        self.serverTransport.listen()
        while self.exit_ent.is_set() is False:
            try :
                client = self.serverTransport.accept()
                if not client:
                    continue
                self.clients.put(client)
            except Exception as x:
                pass
