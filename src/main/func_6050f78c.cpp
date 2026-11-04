extern "C" {

struct Entry {
    char pad0[0x16c0];
    unsigned short field_16c0;
};

struct Root {
    char pad0[0x304];
    Entry *arr[0x17];
};

Entry *func_6050f78c(Root *root, unsigned short val)
{
    for (unsigned int i = 0; i < 0x16; i++) {
        Entry *e = root->arr[i];
        if (e != 0 && e->field_16c0 == val)
            return e;
    }
    return 0;
}

}