struct Next;

struct Vtable {
    unsigned int pad[3];
    void (*fn)(void *, void *);
};

struct Holder {
    void *vptr;
};

struct Caller {
    unsigned int pad[1];
    void *field;
};

extern "C" void func_60123b00(Caller *a, Holder *b)
{
    Vtable *vt = (Vtable *)b->vptr;
    vt->fn(b, a->field);
}