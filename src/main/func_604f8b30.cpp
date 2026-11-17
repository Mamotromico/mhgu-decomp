extern "C" void func_60887160(void *);

extern "C" void func_604f8b30(char *p) {
    func_60887160(p);
    *(unsigned *)(p + 0x64) = 0;
    *(unsigned *)(p + 0x68) = 0;
    *(unsigned *)(p + 0xcc) = 0;
    *(unsigned *)(p + 0xd0) = 0;
}