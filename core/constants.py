from enum import Enum
import os


constants={

            'hid'                       :{
                'speed'                 :{
                    'ultrafast'         :'(0,0)',
                    'faster'            :'(20,10)',
                    'fast'              :'(50,20)',
                    'human-like'        :'(120,40)',
                    'slow'              :'(200,70)'
                }
            },

        }


class HIDspeed(Enum):
    ultrafast=(0, 0)
    faster=(20, 10)
    fast=(50, 20)
    humanlike=(120, 40)
    slow=(200, 70)

    