extern "C" {

extern char D_61897368[];

struct S {
    char pad0[0x34];
    void *(*fn)(void *, void *);
};

struct S *func_607aa47c(void *);

void func_604f7cd8(void *a) {
    void *obj = func_607aa47c(&D_61897368);
    struct S *s = *(struct S **)obj;
    s->fn(obj, a);
}

}