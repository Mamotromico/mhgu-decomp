struct Entry {
    unsigned int pad0;
    unsigned char val;   // offset 0x4
};
struct Outer {
    char pad[0x74];
    unsigned int count;  // offset 0x74
    Entry* arr;          // offset 0x78
};

extern "C" Entry* func_60876a5c(Outer* o, unsigned char target)
{
    unsigned int n = o->count;
    if (n == 0)
        return 0;
    Entry* p = o->arr;
    for (unsigned int i = 0; i < n; i++) {
        if (p->val == target)
            return p;
        p++;
    }
    return 0;
}