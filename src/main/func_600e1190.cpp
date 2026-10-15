struct Foo {
    unsigned int pad0;
    unsigned short flags;
};

extern "C" int func_600e1190(Foo* foo) {
    return foo->flags & 1;
}