// First Entry over the Pool structure whose (a, b, c) all equal the
// zero-extended arguments.
typedef unsigned int  u32;
typedef unsigned char u8;

struct Entry { u8 pad[4]; u8 a; u8 b; u8 c; };
struct Pool  { u8 pad0[0x68]; u32 count; u8 pad1[0x74 - 0x6c]; Entry **arr; };

extern "C" Entry *find3(Pool *p, int a, int b, int c) {
    u32 n = p->count;
    if (n == 0) return 0;
    Entry **arr = p->arr;
    for (u32 i = 0; i < n; i++) {
        Entry *e = arr[i];
        if (e != 0 && e->a == (u8)a && e->b == (u8)b && e->c == (u8)c) return e;
    }
    return 0;
}
