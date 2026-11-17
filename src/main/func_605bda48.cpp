extern "C" void func_6056e3b0(void *);

extern "C" void func_605bda48(char *p) {
    *(unsigned *)(p + 0x28) = 0;
    func_6056e3b0(p);
    *(unsigned *)(p + 0x20) |= 0x1e;
}