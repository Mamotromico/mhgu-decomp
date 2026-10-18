struct S {
    void **vtable;
};

extern "C" void func_611290d0(S *s) {
    reinterpret_cast<void (*)(S *)>(s->vtable[0x1b0 / sizeof(void *)])(s);
}