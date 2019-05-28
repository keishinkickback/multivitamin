from threading import Lock
from abc import ABC, abstractmethod
from multivitamin.media import MediaRetriever
from multivitamin.module.codes import Codes
import _thread
import time

from threading import Thread

from enum import Enum

import glog as log

class States(Enum):
    IRRELEVANT=1
    TO_BE_PROCESSED=2
    PREPARING_TO_BE_PROCESSED=3
    READY_TO_BE_PROCESSED=4
    BEING_PROCESSED=5
    PROCESSED=6

class ResponseFiniteStateMachine(ABC):
    def __init__(self,enablefsm=False):
        self.enabled=enablefsm
        #we instanciate the lock
        self._lock = Lock()
        self._state=States.IRRELEVANT
        self.media=None
        self._downloading_thread=None
        self._downloading_thread_creation_time=None
        self._downloading_thread_timeout=60
    def __del__(self): 
        self.stop_downloading_thread()
        

    def stop_downloading_thread(self):
        log.warning('To be implemented')
        return True
        if self._downloading_thread:
            try:
                self._downloading_thread.exit()                
            except Exception as e:
                log.error("error exiting self._downloading_thread")
                log.error(traceback.format_exc())
        self._downloading_thread=None
        self._downloading_thread_timeout=0

    def check_timeout(self):
        if not self.enabled:
            return False
        if not self.is_preparing_to_be_processed():
            return False
        lifetime=time.time()- self._downloading_thread_creation_time
        if lifetime>self._downloading_thread_timeout:
            log.info("self._downloading_thread_creation_time: " + str(self._downloading_thread_creation_time))
            log.info("lifetime: " + str(lifetime))            
            self.stop_downloading_thread()
            log.warning("ERROR_TIMEOUT")
            self.code = Codes.ERROR_TIMEOUT
            self.set_as_processed()
            return True

    def enablefsm(self):
        self.enabled=True
        if self.is_irrelevant():
            self.set_as_to_be_processed()

    #Updating or checking the state of whichever response is controlled by a lock
    def _update_response_state(self,state):        
        ret=True
        if self.enabled==False:
            return ret
        self._lock.acquire()
        if self._state==state:
            ret=False
        else:
            log.info('From ' + self._state.name + ' to '+ state.name +'.'+ self.url)
        self._state=state
        self._lock.release()
        return ret
    def _check_response_state(self):
        log.info(self._state.name +'.'+ self.url)
        if self.enabled==False:
            return States.IRRELEVANT
        self._lock.acquire()
        state=self._state
        self._lock.release()
        return state

    ################
    def is_irrelevant(self):
        return self._check_response_state()==States.IRRELEVANT
    def is_to_be_processed(self):
        if self.enabled==False:
            return True
        return self._check_response_state()==States.TO_BE_PROCESSED
    def is_preparing_to_be_processed(self):
        if self.enabled==False:
            return True
        return self._check_response_state()==States.PREPARING_TO_BE_PROCESSED
    def is_ready_to_be_processed(self):
        if self.enabled==False:
            return True
        return self._check_response_state()==States.READY_TO_BE_PROCESSED   
    def is_already_processed(self):
        if self.enabled==False:
            return True
        return self._check_response_state()==States.PROCESSED
    #################
    def set_as_to_be_processed(self):
        return self._update_response_state(States.TO_BE_PROCESSED)
    def set_as_preparing_to_be_processed(self):
        return self._update_response_state(States.PREPARING_TO_BE_PROCESSED)   
    def set_as_ready_to_be_processed(self):
        return self._update_response_state(States.READY_TO_BE_PROCESSED)
    def set_as_being_processed(self):
        return self._update_response_state(States.BEING_PROCESSED)
    def set_as_processed(self):
        self._update_response_state(States.PROCESSED)   
    ##############################
    def _download_media(self):
        if self.enabled:
            self._downloading_thread_creation_time=time.time()
            log.info("Creating thread at " + str(self._downloading_thread_creation_time))
            self._downloading_thread=_thread.start_new_thread(ResponseFiniteStateMachine._fetch_media,(self,))
            log.info("Thread created")            
        else:
            self._fetch_media(r)

    @staticmethod
    def _fetch_media(response):
        """Fetches the media from response.request.url
           Careful, you must keep this method threadsafe
        """
        try:
            log.debug("preparing response")
            if not response.media:
                log.info(f"Loading media from url: {response.request.url}")
                response.media = MediaRetriever(response.request.url)
            else:
                log.info(f"media from url: {response.request.url} was already in place.")
            ResponseFiniteStateMachine._parse_media(response)
        except Exception as e:
            log.error(e)
            log.error(traceback.print_exc())
            response.code = Codes.ERROR_LOADING_MEDIA
            response.set_as_processed()#error downloading the image
        response.set_as_ready_to_be_processed()
        return

    @staticmethod
    def _parse_media(response):
        #if it is video or image, we get a frame iterator and we update width and height
        if response.media.is_image or response.media.is_video:
            response.frames_iterator = response.media.get_frames_iterator(
                response.request.sample_rate
            )             
        (width, height) = response.media.get_w_h()
        log.debug(f"Setting in response w: {width} h: {height}")
        response.width = width
        response.height = height