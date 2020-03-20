//
//  TPStaticLibCallTrace.h
//  staticHook
//
//  Created by 吴凯凯 on 2020/3/19.
//  Copyright © 2020 吴凯凯. All rights reserved.
//


#ifndef __arm64__

void stopTrace(void);
void setMaxDepth(int depth);
void setCostMinTime(uint64_t time);

#else

#ifndef MHCallTrace_h
#define MHCallTrace_h

#include <stdio.h>
#include <objc/objc.h>


typedef struct {
    Class cls;
    SEL sel;
    uint64_t costTime; //单位：纳秒（百万分之一秒）
    int depth;
} TPCallRecord;

typedef struct {
    TPCallRecord *record;
    int allocLength;
    int index;
} TPMainThreadCallRecord;

void stopTrace(void);
TPMainThreadCallRecord *getMainThreadCallRecord(void);
void setMaxDepth(int depth);
void setCostMinTime(uint64_t time);



#endif /* MHCallTrace_h */

#endif
