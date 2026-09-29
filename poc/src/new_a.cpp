// Search a u32-counted array (count@0x64, array@0xcc, stride 0x30) for a struct
// whose bytes @0x20 and @0x21 match two u8 arguments.
typedef unsigned char u8;
typedef unsigned int u32;

struct Child {
    u8 pad0[0x20];
    u8 a;
    u8 b;
    u8 pad1[0x30 - 0x22];
};

struct Self {
    u8 pad0[0x64];
    u32 count;
    u8 pad1[0xcc - 0x68];
    Child* arr;
};

extern "C" Child* find4(Self* self, u8 a, u8 b) {
    u32 n = self->count;
    if (n == 0)
        return 0;
    Child* p = self->arr;
    for (u32 i = 0; i < n; i++, p = (Child*)((char*)p + 0x30)) {
        if (p->a == a && p->b == b)
            return p;
    }
    return 0;
}
