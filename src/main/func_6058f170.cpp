extern "C" void func_6056e4d8(void);
extern "C" void func_6058f190(void *);

extern "C" void func_6058f170(char *p) {
    func_6056e4d8();
    func_6058f190(p);
    *(int *)(p + 0x50) = 0;
}