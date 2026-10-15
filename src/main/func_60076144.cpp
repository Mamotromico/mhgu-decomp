typedef struct Top Top;
    typedef struct Sub Sub;

    struct Sub {
        char pad0[0x3dc];
        void (*fn)(Top *);
    };

    struct Top {
        Sub *sub;
    };

    extern "C" void func_60076144(Top *t)
    {
        t->sub->fn(t);
    }