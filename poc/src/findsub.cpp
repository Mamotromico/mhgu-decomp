// Nested search over the Pool structure: outer loop over arr[], inner loop over
// each entry's sub-array, returning the first Sub whose `flags` (u16 @+4) shares
// any bit with `mask`.
typedef unsigned int  u32;
typedef unsigned char u8;
typedef signed char   s8;
typedef unsigned short u16;

struct Sub    { u8 pad[4]; u16 flags; };
struct Entry2 { u8 pad0[4]; s8 a; u8 pad1[0xc - 5]; u32 n; u8 pad2[0x18 - 0x10]; Sub **sub; };
struct Pool2  { u8 pad0[0x68]; u32 count; u8 pad1[0x74 - 0x6c]; Entry2 **arr; };

extern "C" Sub *findsub(Pool2 *p, int a, int mask) {
    u32 n = p->count;
    if (n == 0) return 0;
    Entry2 **arr = p->arr;
    for (u32 i = 0; i < n; i++) {
        Entry2 *e = arr[i];
        if (e == 0) continue;
        if (e->a != a) continue;
        u32 m = e->n;
        if (m == 0) continue;
        Sub **sub = e->sub;
        for (u32 j = 0; j < m; j++) {
            Sub *f = sub[j];
            if (f != 0 && (f->flags & mask) != 0) return f;
        }
    }
    return 0;
}
