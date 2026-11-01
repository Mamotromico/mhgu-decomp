struct sub_600c439c_inner {
    unsigned char pad_0000[0x24f];
    unsigned char flags;          /* +0x24f */
};

struct sub_600c439c_outer {
    unsigned char pad_0000[0x1428];
    struct sub_600c439c_inner *inner;  /* +0x1428 */
};

extern "C" int func_600c439c(struct sub_600c439c_outer *obj, unsigned int bit)
{
    unsigned char v = obj->inner->flags;
    return (v & (1u << bit)) ? 1 : 0;
}