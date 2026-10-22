struct Inner {
    char pad[4];
    int value;
};

struct Outer {
    char pad[0x14];
    Inner **array;
};

extern "C" int func_60059f18(Outer *outer, int index) {
    Inner *item = outer->array[index];
    return item ? item->value : -1;
}