"""Kullanıcıya yönelik güncel yerel çeviri kurulumu; eski Argos kurulumu değildir."""
from core import Segment
from lecture_translation import LectureTranslator

def setup():
    translator=None
    try:
        translator=LectureTranslator(False,print,lambda:False)
        output=[]
        translator.translate([Segment(0,1,'The parameters are pushed onto the stack and the address is stored in a register.')],
                              'tr',lambda row,progress:output.append(row.text))
        print('\nYerel çeviri denemesi:\n'+output[0])
        return 0
    except Exception as error:
        print('\nYerel çeviri kurulumu tamamlanamadı:\n'+str(error))
        return 1
    finally:
        if translator is not None:translator.close()

if __name__=='__main__':raise SystemExit(setup())
