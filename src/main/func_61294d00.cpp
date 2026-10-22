typedef void (*Fn61294d00)(void *);

struct VTable61294d00 {
    char pad_0[0x18];
    Fn61294d00 fn_18;
};

struct Obj61294d00 {
    VTable61294d00 *vtable;
};

struct Mid61294d00 {
    char pad_0[0xc];
    Obj61294d00 *obj;
};

struct Top61294d00 {
    char pad_0[0x9c];
    Mid61294d00 *mid;
};

extern "C" void func_61294d00(Top61294d00 *top) {
    Obj61294d00 *obj = top->mid->obj;
    obj->vtable->fn_18(obj);
}