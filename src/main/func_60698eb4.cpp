struct Inner {
    char pad[4];
    signed char data[1];
};

struct Outer {
    char pad[0x18];
    struct Inner **table;
};

extern "C" signed char func_60698eb4(struct Outer *outer, int index, int offset)
{
    struct Inner *entry = outer->table[index];
    return entry ? entry->data[offset] : (signed char)-1;
}