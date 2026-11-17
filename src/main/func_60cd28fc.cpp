extern "C" int func_60838750(void *);

extern "C" void func_60cd28fc(char *p) {
    *(unsigned *)(p + 0x2c) = func_60838750(p + 0x34);
    *(unsigned *)(p + 0x30) = func_60838750(p + 0x50);
}