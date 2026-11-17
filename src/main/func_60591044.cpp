extern "C" void func_6056e4d8(void *);
extern "C" void func_60591064(void *);

extern "C" void func_60591044(void *p) {
    func_6056e4d8(p);
    func_60591064(p);
    *(unsigned *)((char *)p + 0x50) = 0;
}