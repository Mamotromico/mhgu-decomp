extern "C" void func_60b20400(char *r0, unsigned r1, unsigned r2, unsigned char r3, unsigned char r4, unsigned char r5)
{
    typedef struct { char pad[8]; int counter; } Counter;
    if (r2 != 0) {
        Counter *c = (Counter *)r2;
        int expected;
        int status;
        do {
            expected = __builtin_arm_ldaex(&c->counter);
            expected += 1;
            status = __builtin_arm_stlex(expected, &c->counter);
        } while (status != 0);
    }
    unsigned idx = r1 + r1 * 2;
    char *p = r0 + idx * 4;
    *(unsigned *)(p + 0x18) = r2;
    *(unsigned char *)(p + 0x1c) = r3;
    *(unsigned char *)(p + 0x1d) = r4;
    (void)r5;
}