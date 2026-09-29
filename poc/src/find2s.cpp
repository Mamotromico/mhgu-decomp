// Same Pool as find2.cpp, but the two compared fields are SIGNED bytes and the
// arguments are plain ints (no truncation of the arguments).
typedef unsigned int  u32;
typedef unsigned char u8;
typedef signed char   s8;

struct EntryS { u8 pad[4]; s8 a; s8 b; };
struct PoolS  { u8 pad0[0x68]; u32 count; u8 pad1[0x74 - 0x6c]; EntryS **arr; };

extern "C" EntryS *find2s(PoolS *p, int a, int b) {
    u32 n = p->count;
    if (n == 0) return 0;
    EntryS **arr = p->arr;
    for (u32 i = 0; i < n; i++) {
        EntryS *e = arr[i];
        if (e != 0 && e->a == a && e->b == b) return e;
    }
    return 0;
}
