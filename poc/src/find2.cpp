// Entry search over the Pool structure (see find3.cpp), with two modes:
// mode != 0 accepts entries whose `c` is 0 or 2; mode == 0 accepts `c` in {1, 2}.
typedef unsigned int  u32;
typedef unsigned char u8;

struct Entry { u8 pad[4]; u8 a; u8 b; u8 c; };
struct Pool  { u8 pad0[0x68]; u32 count; u8 pad1[0x74 - 0x6c]; Entry **arr; };

extern "C" Entry *find_entry(Pool *p, int a, int b, int mode) {
    u32 n = p->count;
    if (n == 0)
        return 0;
    Entry **arr = p->arr;
    if (mode != 0) {
        for (u32 i = 0; i < n; i++) {
            Entry *e = arr[i];
            if (e == 0)
                continue;
            if (e->a == (u8)a && e->b == (u8)b) {
                if (e->c == 0 || e->c == 2)
                    return e;
            }
        }
    } else {
        for (u32 i = 0; i < n; i++) {
            Entry *e = arr[i];
            if (e == 0)
                continue;
            if (e->a == (u8)a && e->b == (u8)b) {
                if (e->c - 1 < 2 && e->c != 0)
                    return e;
            }
        }
    }
    return 0;
}
