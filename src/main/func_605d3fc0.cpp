struct Outer {
    char pad[0x64];
    void *obj;
};

typedef void *(*Func)(void *);

extern "C" void *func_605d3fc0(Outer *outer) {
    void *obj = outer->obj;
    if (obj == 0) {
        return 0;
    }
    Func f = *(Func *)(*(char **)obj + 0x8c);
    return f(obj);
}