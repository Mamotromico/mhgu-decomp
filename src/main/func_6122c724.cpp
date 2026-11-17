extern "C" void _ZN2nn2os26BroadcastConditionVariableEPNS0_21ConditionVariableTypeE(void *);
extern "C" void _ZN2nn2os23SignalConditionVariableEPNS0_21ConditionVariableTypeE(void *);

extern "C" void func_6122c724(void *p) {
    void *cv = *(void **)p;
    unsigned char flag = *(unsigned char *)((char *)p + 8);
    if (flag)
        _ZN2nn2os26BroadcastConditionVariableEPNS0_21ConditionVariableTypeE(cv);
    else
        _ZN2nn2os23SignalConditionVariableEPNS0_21ConditionVariableTypeE(cv);
}