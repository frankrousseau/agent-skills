// Safe SVGO settings for the website SVGs, animated ones included.
// Usage: node_modules/.bin/svgo --config .claude/skills/svg-cleanup-pass/svgo.config.mjs -i in.svg -o out.svg
export default {
  multipass: true,
  js2svg: { indent: 2, pretty: true },
  plugins: [
    {
      name: 'preset-default',
      params: {
        overrides: {
          // Animated elements start hidden (opacity 0) and are shown by CSS keyframes.
          removeHiddenElems: false,
          // Class rules carry the animations: keep them in <style>.
          inlineStyles: false,
          minifyStyles: false,
          // Ids are referenced from CSS, <use> and other files: keep them readable.
          cleanupIds: false,
          // Grouping carries classes, transforms and transform-origin for animations.
          collapseGroups: false,
          mergePaths: false,
          moveGroupAttrsToElems: false,
          moveElemsAttrsToGroup: false,
          // The description can be the accessible name of the image.
          removeDesc: false,
          // role="img" and aria-label give the image its accessible name.
          removeUnknownsAndDefaults: { keepRoleAttr: true, keepAriaAttrs: true }
        }
      }
    }
  ]
}
