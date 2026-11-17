extern "C" void func_600fa794(void *self, void **arg) {
    void *obj = *arg;
    int (*fn)(void *) = *(int (**)(void *))((char *)obj + 0xc);
    int result = fn(arg);
    *(int *)((char *)self + 0x4) = result;
}