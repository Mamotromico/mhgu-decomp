extern "C" void func_60887660(void *p);

struct T {
    char pad[0x8d0];
    void *field_8d0;
};

extern "C" void func_603d7474(T *p) {
    void *q = p->field_8d0;
    if (q == 0)
        return;
    func_60887660(q);
    p->field_8d0 = 0;
}