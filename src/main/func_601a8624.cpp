struct S_601a8624 {
    unsigned char pad[0x55c];
    volatile unsigned int v_55c;
    volatile unsigned int v_560;
    volatile unsigned int v_564;
    volatile unsigned int v_568;
    volatile unsigned int v_56c;
    volatile unsigned int v_570;
};

extern "C" void func_601a8624(S_601a8624* s) {
    s->v_55c = 0;
    s->v_560 = 0;
    s->v_564 = 0;
    s->v_568 = 0;
    s->v_56c = 0;
    s->v_570 = 0;
}