struct ClearTarget {
    unsigned char pad0[8];
    volatile unsigned int field_08;
    volatile unsigned int field_0c;
    volatile unsigned int field_10;
    volatile unsigned int field_14;
};

extern "C" void func_60a29750(ClearTarget* p) {
    p->field_08 = 0;
    p->field_0c = 0;
    p->field_10 = 0;
    p->field_14 = 0;
}