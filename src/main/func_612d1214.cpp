struct Foo_612d1214 {
    char pad[0x74];
    int* begin;
    int* end;
};

extern "C" int func_612d1214(Foo_612d1214* foo, unsigned int index, int value) {
    int count = foo->end - foo->begin;
    if ((unsigned int)count > index) {
        foo->begin[index] = value;
    }
    return count;
}