struct VTable {
    char pad[0x30];
    int (*call)(void*, int, int, int);
};

struct Object {
    VTable* vtbl;
};

extern "C" int func_60cebdb8(Object* obj, int arg) {
    return obj->vtbl->call(obj, arg, 0, 1);
}