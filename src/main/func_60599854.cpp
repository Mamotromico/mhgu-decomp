extern "C" void func_60160800(void *, unsigned char);
extern "C" void func_60160640(void *);

extern "C" void func_60599854(void *p) {
    void *v = *(void **)((char *)p + 0x4c);
    if (!v)
        return;
    func_60160800(v, *(unsigned char *)((char *)p + 0x6c));
    func_60160640(*(void **)((char *)p + 0x4c));
}