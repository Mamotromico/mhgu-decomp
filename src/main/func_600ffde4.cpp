struct A {
    char pad0[0xc];
    void *(*fn)(void *);
};

extern "C" void func_600ffde4(void *self, void *arg) {
    A *a = *(A **)arg;
    void *(*fn)(void *) = a->fn;
    *(void **)((char *)self + 4) = fn(arg);
}